module abs_diff_i916_o458(a,b,r);
input [457:0] a,b;
output [457:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
