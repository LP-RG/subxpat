module abs_diff_i268_o134(a,b,r);
input [133:0] a,b;
output [133:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
