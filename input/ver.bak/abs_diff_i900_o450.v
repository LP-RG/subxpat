module abs_diff_i900_o450(a,b,r);
input [449:0] a,b;
output [449:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
