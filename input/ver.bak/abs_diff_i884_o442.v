module abs_diff_i884_o442(a,b,r);
input [441:0] a,b;
output [441:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
