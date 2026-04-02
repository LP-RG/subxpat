module abs_diff_i236_o118(a,b,r);
input [117:0] a,b;
output [117:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
