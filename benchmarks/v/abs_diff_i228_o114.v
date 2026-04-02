module abs_diff_i228_o114(a,b,r);
input [113:0] a,b;
output [113:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
