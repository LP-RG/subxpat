module abs_diff_i360_o180(a,b,r);
input [179:0] a,b;
output [179:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
