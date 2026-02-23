module abs_diff_i824_o412(a,b,r);
input [411:0] a,b;
output [411:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
