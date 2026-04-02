module abs_diff_i100_o50(a,b,r);
input [49:0] a,b;
output [49:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
