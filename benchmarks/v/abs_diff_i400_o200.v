module abs_diff_i400_o200(a,b,r);
input [199:0] a,b;
output [199:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
