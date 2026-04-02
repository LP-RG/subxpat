module abs_diff_i968_o484(a,b,r);
input [483:0] a,b;
output [483:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
