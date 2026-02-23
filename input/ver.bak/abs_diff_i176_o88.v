module abs_diff_i176_o88(a,b,r);
input [87:0] a,b;
output [87:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
